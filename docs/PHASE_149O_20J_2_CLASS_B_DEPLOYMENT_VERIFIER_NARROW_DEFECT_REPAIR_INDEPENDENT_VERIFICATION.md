# Phase 149O.20J.2 — Class-B Deployment Verifier Narrow Defect Repair
Independent Verification

**Status:** Independent verification complete. **INDEPENDENT REPAIR
VERIFICATION ONLY** — no production source, contract, or script file
modified; no repair performed; no HMIC source-scope evolution; no
Class-B provisioning; no readiness/certification/activation change.
Verifier source remains outside HMIC's frozen 25-file identity;
`COMPLIANT` remains diagnostic-only.

## 0. Baseline

Phase entry is 149O.20J.1's own exit state: repo clean, `origin/main..
HEAD = 0`, commits `0f2bb93c` (repair), `c68d1ee7`/`34385cbb` (metadata
sync), pushed. Independently re-confirmed via `pcae health`, `pcae
check`, `pcae status coherence`, `pcae doctor task-memory`, `pcae push
check`, `pcae runtime inspect`, `pcae notify status`, `pcae phase-report
show --latest`, `pcae phase-report reconcile --phase-id 149O.20J.1`:
health/check/coherence all pass; runtime `Observed / observe /
unavailable`; canonical report confirms 149O.20J.1 complete and
recommends 149O.20J.2 next; reconciliation reports `status: reconciled`,
`mutation: none (inspection only)`. `pcae doctor task-memory` shows
pre-existing, unrelated `tasks/active/`/`tasks/DONE.md` bookkeeping
warnings carried forward across many prior phases — not new to this
phase and not blocking (task memory is documentation-only, not a
governance gate).

## 1. J.1 Production Diff — Independently Reconstructed

`git diff --stat 0f2bb93c^ 0f2bb93c` and `git rev-parse 0f2bb93c^`
independently confirm the pre-repair baseline commit is `dce667e7`
(149O.20J's own close-idle commit) and that the diff touches exactly:

- `src/pcae/core/hatp_class_b_topology_verifier.py` (+50/-5)
- `src/pcae/core/hatp_environment_lock_verifier.py` (+37/-5)

`hatp_class_b_conformance.py`: `git diff --name-only 0f2bb93c^ HEAD --
src/pcae/core/hatp_class_b_conformance.py` returns empty — confirmed
byte-unchanged, independently, not merely accepted from 149O.20J.1's
prose.

Hunk classification (read from the actual diff, not from 149O.20J.1's
description):

| Hunk | Classification |
|---|---|
| `_current_agent_identity` union with `os.getegid()` | EFFECTIVE_GID_REPAIR |
| New `_resolve_trusted_executable_with_effective_access` function | TRUSTED_GIT_ACL_REPAIR |
| Import swap `_resolve_trusted_executable` → `..._with_effective_access` | TRUSTED_GIT_ACL_REPAIR |
| New `_pth_line_is_executable` + `_check_pth_files` call-site swap | PTH_EXECUTABLE_GRAMMAR_REPAIR |
| `_check_trusted_git` docstring + call-site swap | TRUSTED_GIT_ACL_REPAIR |

**UNRELATED = 0.** Matches 149O.20J.1's own claim, independently
re-derived.

## 2. J-1 — Historical Reproduction and CPython `.pth` Semantics

Read the real, running interpreter's `site.addpackage()` source
directly (`inspect.getsource(site.addpackage)`, CPython 3.14.5) — not
inferred from prose. Confirmed classification order: `#`-prefixed line
→ comment (skip); all-whitespace line → blank (skip); otherwise
`line.startswith(("import ", "import\t"))` on the **raw, unstripped**
line → `exec(line)`; anything else → path entry.

Reconstructed the pre-repair predicate from `dce667e7`'s actual source
(`line.strip().startswith("import ")`) and cross-tested it against this
independently-derived CPython rule over an adversarial matrix (tab
form, double space/tab, leading space/tab, bare `import`, no-separator,
case variant, CR/LF/VT/FF variants, comment-with-import, blank,
safe-path): **the historical predicate misses `"import\tfoo"`**
(CPython executes it; predicate returns `False`) **and over-flags
`"  import foo"`** (predicate returns `True`; CPython does not execute
it, since `startswith` runs on the raw, unstripped line). Both defects
independently reproduced.

Directly proved CPython execution (not merely predicted) by calling
`site.addpackage()` against a scratch `.pth` file containing a
tab-delimited `import` line and observing the exec side effect fire.

Live repaired `_pth_line_is_executable` tested against the same
17-case adversarial matrix derived from the independently-confirmed
CPython rule: **zero mismatches.** The full `_check_pth_files`
function was exercised (via monkeypatched `_effective_sys_path_dirs`/
`_effective_write_access`) against four fixtures in one pass: a
comment-only mention of "import" (not flagged), a plain safe path line
(not flagged), a tab-import executable line in an otherwise
agent-unwritable file (flagged — the decisive J-1 test), and an
agent-writable file with harmless content (flagged for writability
regardless of content) — confirming the repair neither regresses
comment-handling nor the writability-based path-injection defense.

**J-1 verdict: INDEPENDENTLY CONFIRMED CLOSED** (at the
non-authoritative verifier-implementation boundary — see §11).

## 3. J-2 — Historical Reproduction and Effective-GID Repair

Reconstructed the pre-repair `_current_agent_identity` from `dce667e7`'s
actual source (`return os.geteuid(), frozenset(os.getgroups())`) and
confirmed the string `"os.getegid()"` is absent from that historical
source. Reproducing it directly (`os.getgroups` mocked to `[10, 20]`,
`os.getegid` mocked to `30`): historical function returns a group set
that omits `30`. The repaired function (live, current source) applied
to the identical mock returns `{10, 20, 30}` — `os.getegid()`
independently folded in via set union, confirmed directly from the
running production function, not an inlined copy.

Effective-group matrix (item 14), against the live repaired function:

| Case | `getgroups()` | `getegid()` | Expected | Got |
|---|---|---|---|---|
| A | `[10,20]` | `30` | `{10,20,30}` | `{10,20,30}` ✓ |
| B | `[10,20,30]` | `30` | `{10,20,30}` | `{10,20,30}` ✓ |
| C | `[]` | `30` | `{30}` | `{30}` ✓ |

Duplicate-safety (item 17): `getgroups=[30,30,10]`, `getegid=30` →
`frozenset({10, 30})`, confirming `frozenset` set semantics dedupe
correctly. Source-level check (item 16) confirms
`_current_agent_identity` calls `os.getegid()` and never
`os.getgid()` (real gid is never substituted for effective gid).

**Decisive permission attack (item 15):** built a fixture file (group
`= 30`, mode `0o060`, group-write granted) and, with the ACL sub-check
forced to report "no ACL" (isolating the mode+group channel exactly),
compared `_effective_write_access` under the historical group set
(`{10, 20}`, excluding the effective GID) versus the repaired group set
(`{10, 20, 30}`): **historical → `write=False` (would incorrectly pass
as no-write-access); repaired → `write=True,
reason=agent_group_membership_grants_write` (correctly detects the
write authority).** This isolates and confirms the exact defect/repair
pair, independent of any ACL-branch interaction.

**J-2 verdict: INDEPENDENTLY CONFIRMED CLOSED** (at the
non-authoritative verifier-implementation boundary — see §11).

## 4. J-3 — Trusted-Git ACL Repair

Confirmed from `dce667e7`'s actual source that the pre-repair
`_check_trusted_git` calls `_resolve_trusted_executable("git")`
directly — a function that internally uses only
`_mode_and_group_write_access` (mode + group-membership, never ACL).

**Historical blindness reproduced:** built a Git-executable fixture
with safe mode bits (`0o500`, no group/other write) on both the file
and its containing directory, then simulated an ACL-only write grant on
the executable (`_acl_grants_agent_write` monkeypatched to report `True`
for that exact path). The narrow, pre-repair-equivalent
`_resolve_trusted_executable` still resolved (trusted) the executable —
confirming it never consults ACL evidence at all.

**Repaired wrapper verification** (`_resolve_trusted_executable_
with_effective_access`), same ACL-only-grant fixture: **rejected
(`None`)** — the wrapper's `_effective_write_access` call surfaces the
simulated ACL grant and the executable is correctly untrusted.

**Attack matrix, all against the live repaired wrapper:**

| Attack | Result |
|---|---|
| Git executable ACL-only write grant | REJECTED |
| Git immediate-parent ACL-only write grant | REJECTED |
| Git deep ancestor (2 levels up) ACL-only write grant, immediate parent proven safe by mode | **NOT REJECTED** — see §5 |
| PATH-preceding agent-writable directory (no git present there) | REJECTED |
| Fake git placed in an earlier agent-writable PATH directory | REJECTED (regression of the pre-existing fake-Git defense; unaffected by J.1) |
| ACL tool inspection returns indeterminate (`None`) | REJECTED (fail-closed; never interpreted as "no ACL") |

**Non-recursion — proven two ways.** Static: built the module's call
graph via `ast.walk` over every relevant function
(`_resolve_trusted_executable_with_effective_access`,
`_resolve_trusted_executable`, `_effective_write_access`,
`_acl_grants_agent_write[_linux|_macos]`, `_ancestor_chain_safe`,
`_mode_and_group_write_access`) and searched for any path leading back
to the wrapper itself: **none found.** The wrapper calls the narrow
`_resolve_trusted_executable`, `_effective_write_access`, and
`_ancestor_chain_safe`; the ACL branch (`_acl_grants_agent_write_linux`/
`_macos`) resolves its own tool (`getfacl`/`ls`) exclusively through
the narrow `_resolve_trusted_executable`, never through the wrapper.
Dynamic: monkeypatched the wrapper itself to raise on any re-entrant
call and directly exercised the real ACL branch (`_acl_grants_agent_
write`) against a resolvable git fixture — the poisoned wrapper's call
counter stayed at `0` throughout, confirming the ACL-tool-resolution
path never re-enters the wrapper.

**ACL evidence mechanism (item 19/21):** Linux uses `getfacl -p
<path>` (parses `user:`/`group:`/`mask:`/`other:` ACL entry lines for a
`w` permission matching the agent's uid/gids); macOS uses `ls -lde
<path>` (checks for the `+` ACL marker on the mode string, then scans
subsequent lines for a `write`/`allow write` entry). **The ACL tool
is external** in both cases, resolved via the narrow,
non-recursive PATH-precedence walk (`_resolve_trusted_executable`) —
not a fixed/canonical hardcoded path — and is itself checked only by
mode+group (deliberately, disclosed, to avoid recursion), so an
ACL-only write grant on `getfacl`/`ls` themselves would not be
independently detected by this mechanism; this residual, disclosed
trade-off is unchanged by J.1 (it predates this phase entirely) and is
not one of the three named defects.

**Topology/Git effective-access equivalence (item 29):** the wrapper's
own source directly calls both `_effective_write_access` and
`_ancestor_chain_safe` — the exact same primitives backing Protected
Root's HBDC-REQ-016/017 checks. No divergent, independently-maintained
policy exists for Git versus topology.

**Repaired-group-semantics composition (item 30):** the wrapper calls
`_current_agent_identity()` directly (confirmed by source inspection)
— the same repaired function verified in §3 — so Git-path decisions use
the identical, centralized, `os.getegid()`-inclusive effective-group
derivation; no separate or stale group calculation exists for Git.

**J-3 verdict: INDEPENDENTLY CONFIRMED CLOSED** for the specific
disclosed defect (ACL blindness) — see §5 for the one residual,
out-of-scope observation.

## 5. One Non-Blocking Observation (Not a J-3 Regression)

The shared `_ancestor_chain_safe` primitive stops its upward walk at
the **first** ancestor directory proven non-writable (a "safe
boundary") and does not examine further ancestors above that point.
Concretely: with a Git executable's immediate parent proven safe by
mode bits alone, a *grandparent* directory that is agent-writable is
never examined and the resolution is accepted.

This is independently reproduced against the live production code (see
the test module, `test_git_deep_ancestor_acl_only_grant_bounded_by_
first_safe_boundary`), but it is **not a J.1 regression and not one of
the three named B-CBV-J-1/2/3 defects**:

- `_ancestor_chain_safe` is **unmodified** by J.1 (confirmed by the
  diff reconstruction in §1) — it is the same shared primitive already
  used, identically, by Protected Root's own HBDC-REQ-017 check since
  149O.20I.
- This exact scenario was already independently constructed and
  disclosed by 149O.20J's own frozen test suite
  (`test_deep_ancestor_writable_beyond_immediate_parent_is_caught`),
  whose docstring explicitly documents the stop-at-first-safe-boundary
  design and asserts `safe is True` as the *intended* behavior — this
  phase did not discover a new gap, it independently re-confirmed a
  pre-existing, already-disclosed one.
- Item 29's topology/Git equivalence is actually *reinforced* by this
  finding: because both call sites share the one primitive, this
  characteristic is identical (not divergent) between Protected Root
  and Git.
- J.1's own B-CBV-J-3 defect was specifically "checks only mode+group,
  never ACL at all" — fully repaired (§4). The first-safe-boundary
  walk semantics is an orthogonal, pre-existing property of a shared
  ancestor-walk primitive, outside this narrow repair's named scope.

**Disposition:** recorded as a Non-Blocking, pre-existing observation.
Recommend a future, separately-governed phase re-examine whether
HBDC-REQ-017's "up to the point the agent principal has no write access
at all" wording is best read as "stop at the first non-writable
ancestor" (current implementation) or "every ancestor must be
non-writable, all the way to a true root boundary" (the stricter
reading under which a writable grandparent behind a safe parent would
still be unsafe, since removing/renaming a directory entry requires
write on its *containing* directory, not on the entry itself). This
question applies identically to Protected Root and Git and is **not**
introduced, widened, or narrowed by 149O.20J.1 or this verification
phase.

## 6. Cross-Cutting Verification

- **Read-only static scan:** `ast.walk` over all three modules for a
  forbidden-mutation-attribute set (`mkdir`, `chmod`, `chown`,
  `unlink`, `rename`, `symlink`, `link`, `write_bytes`, `setuid`, etc.)
  found **zero** matches. The one incidental `.replace(` hit in
  `hatp_environment_lock_verifier.py` line 316 is `str.replace("/",
  ".")` (module-name string transform), independently confirmed not a
  filesystem `Path.replace`.
- **Read-only behavioral check:** invoked
  `verify_class_b_deployment_conformance()` against the real,
  unprovisioned host; `git status --short` before and after are
  byte-identical (only this phase's own two untracked task/test files
  present, unaffected by the invocation).
- **Real-host result:** `NON_COMPLIANT` (not `COMPLIANT`) — expected,
  unprovisioned host, no mutation.
- **Subprocess inventory:** exactly 2 `subprocess.run(` call sites in
  `hatp_class_b_topology_verifier.py`, both pre-existing (`getfacl -p`,
  `ls -lde`; independently confirmed present in the pre-repair
  `dce667e7` source at the same count) — J.1 introduces **zero** new
  subprocess invocations; both use fixed argument lists, a 5s timeout,
  and `stdin=DEVNULL`.
- **Zero production authority consumers:** repository-wide search
  (`rglob("*.py")` over `src/pcae/`, excluding the three modules
  themselves) for the three module names returns **zero** files.
  Individually re-confirmed absent from `hatp_mandatory_cutover.py`,
  `hatp_mandatory_certification.py`, `scripts/hatp_certification_
  admin.py`, `permission_broker.py`, and `hatp_rollback_consumption.py`.
- **HMIC non-binding:** freshly extracted the live
  `_FROZEN_AUTHORITY_BEARING_FILES` constant from
  `hatp_mandatory_certification.py`: exactly 25 entries; none of the
  three verifier module names present.
- **Status vocabulary stability:** `ClassBConformanceStatus` remains
  the same 6-member closed set (`COMPLIANT`, `NON_COMPLIANT`,
  `INDETERMINATE`, `ACCESS_ERROR`, `MALFORMED_STATE`,
  `UNSUPPORTED_DEPLOYMENT_MODEL`); `COMPLIANT` remains the sole
  positive.
- **Public signature stability:** `verify_class_b_topology_conformance`
  and `verify_environment_lock_conformance` remain zero-parameter;
  `verify_class_b_deployment_conformance` remains a single, neutral
  `root: Optional[HarnessPath] = None` locator, never a caller-supplied
  authority boolean.
- **Fail-closed aggregation regression:** an all-satisfied fixture
  yields `COMPLIANT`; every single-check-failure fixture (5 checks,
  failure rotated through each position) yields non-`COMPLIANT`;
  `_safe_check` wrapped around a raising function yields a
  `satisfied=False` result, never a silent pass.
- **20I self-caught fix #1 (meta_path class-vs-instance):**
  re-attacked directly — a fake class-based finder and a fake
  instance-based finder installed on `sys.meta_path` are both
  correctly flagged by `_check_meta_path_hooks`.
- **20I self-caught fix #2 (env/PATH distinction):** re-attacked
  directly — `_check_no_env_or_name_based_admin_inference` reports
  `satisfied=True`; reading `PATH` for `_resolve_trusted_executable` is
  confirmed present in source and correctly not flagged as
  admin-identity inference.

## 7. Independent Test Module

Created `tests/test_phase_149o_20j_2_class_b_deployment_verifier_
narrow_defect_repair_independent_verification.py` (56 tests, all
passing). Historical-defect tests read the pre-repair source via `git
show dce667e7:<path>` directly (never an inlined copy); live-repair
tests call the current production functions directly (never 149O.20J
or 149O.20J.1's own test constants/helpers as oracle). One test's own
first draft (`test_git_deep_ancestor_acl_only_grant_bounded_by_first_
safe_boundary`) initially asserted the wrong outcome because its PATH
fixture excluded a real `ls`/`getfacl` resolution path, causing the ACL
sub-check to report indeterminate rather than a genuine safe boundary
and masking the actual behavior under test; corrected to include a real
system bin directory on `PATH` so the ACL tool resolves for real,
reproducing the same result independently confirmed by manual
inspection (§5).

## 8. Regression Results

| Suite | Result |
|---|---|
| New 149O.20J.2 independent suite | 56 passed, 0 failed |
| 149O.20J.1's own suite (regression only) | 26 passed, 0 failed |
| 149O.20J's own suite (regression only) | 61 passed, 1 skipped, 1 failed (disclosed — `test_agent_effective_gid_not_in_getgroups_can_be_missed`, a finding-confirmation test superseded now that the gap it documented is closed, per its own docstring; unmodified per historical-snapshot-preservation discipline) |
| 149O.20I suites (regression only) | 98 passed, 0 failed |
| 149O.20H suite (regression only) | 21 passed, 0 failed |
| Broad sweep (`-k "class_b or hbdc or hmic or 149o_20"`) | 45 failed / 1188 passed / 5 skipped / 1 error — identical failure set (content and count) with this phase's two new files stashed out, confirmed via direct diff; **zero new failures attributable to this phase** |
| Fast Green (`-m fast_green -n auto`) | ~70-71 failed / ~6744-6745 passed / 5 skipped / 1 error (small ±1 delta consistent with known `pytest-xdist` worker-count/collection-order variance, not a new failure — none of this phase's 56 new tests appear in either run's failure list, confirmed directly) |

All broad-sweep and Fast Green failures are the same pre-existing,
unrelated categories already disclosed by prior phases: dirty-tree
snapshot checks tied to historical commit ranges, pinned
requirement/attack-count assertions from older HMIC phases (149O.19.x),
the pre-existing `fido2`-import collection error
(`test_phase_149o_7_...`), and the one disclosed 20J regression above.

## 9. Governance Close Checks

`pcae health`: healthy, active task
`20260812-1706-phase-149o-20j-2-...`, agent lock held by `claude-local`.
`pcae check`: passed (tests/docs/tasks zones touched, matching this
phase's own Allowed Files). `pcae status coherence`: coherent. `pcae
push check`: clean prior to finalization; task-memory pre-existing
warnings carried forward, unrelated. `pcae runtime inspect`: unchanged,
`Observed / observe / unavailable`. `pcae notify status`: Telegram
configured/enabled, ready for dispatch on `phase complete`.

## 10. Findings

**Blocking:** none.

**Non-Blocking:** one — §5's pre-existing, already-disclosed ancestor-
walk stop-boundary characteristic, shared identically by Protected Root
and Git, unmodified by J.1, not one of the three named defects.
Recommend a future phase re-examine HBDC-REQ-017's exact reading.

**Observations:** the ACL tool itself (`getfacl`/`ls`) is trusted only
by mode+group, not ACL-aware (deliberate, disclosed, avoids recursion)
— same disposition already recorded by 149O.20J.1 §5, independently
re-confirmed here, unrelated to the three named defects.

## 11. J-1/J-2/J-3 Exit Status

- **J-1:** INDEPENDENTLY CONFIRMED CLOSED — CLOSED AT NON-AUTHORITATIVE
  VERIFIER IMPLEMENTATION BOUNDARY.
- **J-2:** INDEPENDENTLY CONFIRMED CLOSED — CLOSED AT NON-AUTHORITATIVE
  VERIFIER IMPLEMENTATION BOUNDARY.
- **J-3:** INDEPENDENTLY CONFIRMED CLOSED — CLOSED AT NON-AUTHORITATIVE
  VERIFIER IMPLEMENTATION BOUNDARY.

Qualification: all three are closed strictly at the non-authoritative
verifier-implementation boundary, because HMIC source-scope binding and
readiness/certification consumption have not occurred and are not
authorized by this phase.

## 12. CBV-S1 / CBV-S10

**CBV-S1: VERIFIER IMPLEMENTATION INDEPENDENTLY VERIFIED — HMIC
SOURCE-SCOPE BINDING REQUIRED NEXT — NOT CLOSED.** All three repairs
independently verify; current-state safety (unbound source, zero
authority consumers) re-confirmed (§6). CBV-S1 itself remains open —
this phase does not, and is not authorized to, evolve HMIC's source
scope.

**CBV-S10: READINESS CONTRACT/INTEGRATION GAP REMAINS — NOT CLOSED.**
No readiness contract or integration code was touched or evaluated by
this phase.

## 13. Verification Verdict

```
CLASS-B DEPLOYMENT VERIFIER / MODEL-A ENVIRONMENT-LOCK:
INDEPENDENTLY VERIFIED IN REPAIRED NON-AUTHORITATIVE MODE
— 3/3 BLOCKING DEFECTS INDEPENDENTLY CLOSED
— READ-ONLY
— FAIL-CLOSED
— ZERO PRODUCTION AUTHORITY CONSUMERS
— SOURCE NOT YET HMIC-BOUND
— POSITIVE CONSUMPTION REMAINS FORBIDDEN
```

**Class-B:** CONTRACT VERIFIED — VERIFIER IMPLEMENTATION INDEPENDENTLY
VERIFIED — NOT PROVISIONED.
**HATP:** NOT READY.

## 14. Recommended Next Phase

**149O.20K — HMIC Class-B Verifier Source-Scope Contract Evolution.**
Must NOT assume the target scope grows from 25 to a fixed number
without first performing a fresh transitive authority-dependency
closure over the three verifier modules under HMIC-REQ-052 to determine
the exact required target set (only the three modules if no further
PCAE-owned authority-sensitive dependency is reachable from them;
otherwise those additional files too). 149O.20K itself must be contract
evolution only — no production scope alignment, no readiness
integration, no provisioning in the same phase. Sequence after 149O.20K:
independent contract verification → production HMIC scope alignment →
independent production alignment verification → only then address
CBV-S10's readiness contract/integration gap. **Not started, not
authorized by this phase.**
